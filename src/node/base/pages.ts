import {
    FilePageFrontmatter,
    FolderPageFrontmatter,
    PageFileData,
    PageFilesInfo,
    PageFolderDataNoChildrenData,
} from "../../type/index.js";
import { App, createPage, Page } from "vuepress";
import { File, Folder, isFile } from "./files.js";

/**
 * 给文件创建页面
 * */
export function createFilePage(app: App, path: string, file: File): Promise<Page> {
    const frontmatter: FilePageFrontmatter = {
        layout: 'File',
        title: file.name,
        flistData: {
            name: file.name,
            updateTime: file.updateTime,
            size: file.size,

            downloadUrl: file.downloadUrl,
            downloadCorsAllow: file.downloadCorsAllow,
            contentType: file.contentType,
            content: file.content,
        },
    }
    return createPage(app, {
        path: path,
        frontmatter: frontmatter
    })
}

/**
 * 给文件夹创建页面
 * */
export function createFolderPage(app: App, path: string, folder: Folder): Promise<Page> {
    const childrenData = folder.children.map((children): PageFileData | PageFolderDataNoChildrenData => {
        const base: PageFilesInfo = {
            name: children.name,
            size: children.size,
            updateTime: children.updateTime,
        }
        if (isFile(children)) {
            return {
                ...base,
                downloadUrl: (children as File).downloadUrl,
                downloadCorsAllow: (children as File).downloadCorsAllow,
                contentType: (children as File).contentType
            }
        }
        return {
            ...base,
            isFolder: true
        }
    })

    childrenData = childrenData.sort((a, b) => {
    return new Date(b.updateTime).getTime() - new Date(a.updateTime).getTime();
    });

    // 检查 folder.content 是否为 undefined，如果是则设置为空字符串
    const content = folder.content || '';
    
    const cleanedContent = content
      .replace(/<p[^>]*>.*?<\/p>/gs, '') // 去除 <p> 标签
      .replace(/<samp[^>]*>(.*?)<\/samp>/gs, '$1'); // 去除 <samp> 标签，保留内容

    // console.log(cleanedContent, 123456)
    
    const frontmatter: FolderPageFrontmatter = {
        layout: 'Folder',
        title: folder.title,
        flistData: {
            name: folder.name,
            size: folder.size,
            updateTime: folder.updateTime,
            children: childrenData,
            isFolder: true,
            content: cleanedContent,
        },
    }
    return createPage(app, {
        path: path,
        frontmatter: frontmatter,
    })
}

function createFileTreePagesInner(app: App, path: string, folder: Folder): Promise<Page>[] {
    const pagePromiseList: Promise<Page>[] = [];
    pagePromiseList.push(createFolderPage(app, path + "/", folder));
    //给子文件夹和文件创建页面
    for (let children of folder.children) {
        //如果是文件夹则递归
        if (!isFile(children)) {
            pagePromiseList.push(...createFileTreePagesInner(app, path + "/" + children.name, children as Folder))
            continue;
        }
        //如果是文件则给文件创建
        pagePromiseList.push(createFilePage(app, path + "/" + children.name + "/", children as File));
    }
    return pagePromiseList;
}

/**
 * 创建文件树全部页面
 * */
export function createFileTreePages(app: App, folder: Folder): Promise<Page>[] {
    return createFileTreePagesInner(app, "", folder);
}
